from orchestrator.models import SessionState
from orchestrator.routes.intake import route_intake
from orchestrator.routes.grounding import route_grounding
from orchestrator.routes.user_choice import route_user_choice
from orchestrator.routes.normal import route_normal_execution

from memory_manager.enums import MemoryQueryResult
from uncertainty_engine.enums import UncertaintyLevel
from pacing_controller.enums import PacingMode

from orchestrator.context import OrchestratorContext


class ConversationOrchestrator:
    """
    Deterministic coordination brain of the system.

    Responsibilities:
    - Gather signals (memory, uncertainty)
    - Decide routing
    - Coordinate downstream components
    - Mutate session state ONLY where explicitly allowed

    Never:
    - Decide policy
    - Validate output
    - Write memory
    - Touch model internals
    """

    def __init__(
        self,
        memory_manager,
        uncertainty_engine,
        pacing_controller,
        llm_executor,
        output_validator,
        policy_engine,
    ):
        self.memory_manager = memory_manager
        self.uncertainty_engine = uncertainty_engine
        self.pacing_controller = pacing_controller
        self.llm_executor = llm_executor
        self.output_validator = output_validator
        self.policy_engine = policy_engine

    # ------------------------------------------------------------------
    # STEP 10.3 — PRE-ROUTING (T0 → T2)
    # ------------------------------------------------------------------

    def pre_route(self, session: SessionState, user_input: str):
        """
        Signal gathering phase.
        No routing. No execution.
        """

        # T0 — start of turn
        session.turn_index += 1

        # T1 — memory query
        memory_result = self.memory_manager.query_memory(user_input)

        uncertainty = None

        # T2 — uncertainty evaluation (only if memory is not EMPTY)
        if memory_result != MemoryQueryResult.EMPTY:
            uncertainty = self.uncertainty_engine.evaluate(
                user_input,
                memory_result
            )
            session.active_context = self.uncertainty_engine.last_context

        return memory_result, uncertainty

    # ------------------------------------------------------------------
    # STEP 10.4 — ROUTING DECISION (PURE, NO MUTATION)
    # ------------------------------------------------------------------

    def decide_route(self, memory_result, uncertainty):
        """
        Canonical routing decision logic (LOCKED).
        No mutation allowed here.
        """

        # ROUTE 1: INTAKE
        if memory_result == MemoryQueryResult.EMPTY:
            return "INTAKE"

        # ROUTE 2: GROUNDING — memory conflict ALWAYS wins
        if memory_result == MemoryQueryResult.CONFLICT:
            return "GROUNDING"

        # ROUTE 2: GROUNDING — high uncertainty
        if uncertainty in (
            UncertaintyLevel.LEVEL_4,
            UncertaintyLevel.LEVEL_5,
        ):
            return "GROUNDING"

        # ROUTE 3: USER CHOICE
        if uncertainty == UncertaintyLevel.LEVEL_3:
            return "USER_CHOICE"

        # ROUTE 4: NORMAL EXECUTION
        return "NORMAL"

    # ------------------------------------------------------------------
    # STEP 10.8 — POLICY-DRIVEN MODE ASSIGNMENT
    # ------------------------------------------------------------------

    def assign_mode_if_applicable(self, session: SessionState, uncertainty):
        """
        Apply policy mode recommendation ONLY when allowed.
        """

        if uncertainty in (
            UncertaintyLevel.LEVEL_1,
            UncertaintyLevel.LEVEL_2,
        ):
            session.mode = self.policy_engine.recommend_mode(
                uncertainty_level=uncertainty
            )

    # ------------------------------------------------------------------
    # STEP 10.9 — NORMAL EXECUTION ORCHESTRATION
    # ------------------------------------------------------------------

    def execute_normal(
        self,
        session: SessionState,
        user_input: str,
        uncertainty,
    ):
        """
        Full NORMAL execution pipeline.
        This is the ONLY route that returns plain text.
        """

        # Mode must already be set
        limits = self.pacing_controller.get_limits(session.mode)

        llm_result = self.llm_executor.execute(
            instruction=self.pacing_controller.build_mode_instruction(session.mode),
            user_input=user_input,
            context_block=self.memory_manager.render_relevant_memory(),
            token_limit=limits.hard_cap_tokens,
            mode=session.mode,
            forbidden_patterns=self.policy_engine.get_forbidden_patterns(),
            turn_index=session.turn_index,
        )

        pacing_decision = self.pacing_controller.evaluate_output(
            session.mode,
            llm_result.text,
        )

        # Construct OrchestratorContext (OWNED HERE)
        context = OrchestratorContext(
            uncertainty_level=uncertainty,
            memory_write_attempted=self.memory_manager.write_attempted,
            memory_confirmation_asked=self.memory_manager.confirmation_requested,
            memory_scope=self.memory_manager.last_scope,
            token_count=llm_result.token_usage_output,
            token_limit=limits.hard_cap_tokens,
            user_intent=self.uncertainty_engine.last_intent_summary,
            assumptions_required=self.uncertainty_engine.assumptions_required,
            contains_medium_or_low_confidence_claims=(
                self.output_validator.scan_confidence_levels(llm_result.text)
            ),
        )

        validation = self.output_validator.validate(
            llm_result.text,
            context,
        )

        # Validation rejection → grounding (automatic, no exposure)
        if validation.status == "REJECTED":
            return route_grounding(
                self.policy_engine,
                reason="validation_violation",
            )

        # Deliberative continuation handling
        if session.mode == PacingMode.DELIBERATIVE:
            if pacing_decision.must_continue:
                session.deliberative_turn_count += 1
                return {
                    "type": "DELIBERATIVE_CONTINUE",
                    "message": "Continue?",
                    "turn_index": session.turn_index,
                }
            else:
                session.deliberative_turn_count = 0

        # ✅ NORMAL execution returns raw text ONLY
        return llm_result.text

    # ------------------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ------------------------------------------------------------------

    def handle_turn(self, session: SessionState, user_input: str):
        """
        Single authoritative turn handler.
        """

        memory_result, uncertainty = self.pre_route(session, user_input)
        route = self.decide_route(memory_result, uncertainty)

        if route == "INTAKE":
            return route_intake(self.policy_engine)

        if route == "GROUNDING":
            reason = (
                "memory_conflict"
                if memory_result == MemoryQueryResult.CONFLICT
                else "high_uncertainty"
            )
            return route_grounding(self.policy_engine, reason=reason)

        if route == "USER_CHOICE":
            return route_user_choice(self.policy_engine)

        # NORMAL EXECUTION
        self.assign_mode_if_applicable(session, uncertainty)
        return self.execute_normal(session, user_input, uncertainty)