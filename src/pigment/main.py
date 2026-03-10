# Entry point — run this to launch Pigment
import sys
from pigment.app import PigmentApp

def main():
    app = PigmentApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    sys.exit(main())
