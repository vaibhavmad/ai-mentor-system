import sys
from policy_engine.policy_engine import PolicyEngine
from policy_engine.errors import PolicyValidationError


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m policy_engine <policy_path>")
        sys.exit(1)

    policy_path = sys.argv[1]

    try:
        PolicyEngine(policy_path)
        print("Policy validation successful.")
        sys.exit(0)

    except FileNotFoundError:
        print("Policy file not found.")
        sys.exit(2)

    except ValueError as e:
        print(str(e))
        sys.exit(3)

    except PolicyValidationError as e:
        print(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()