import sys

if len(sys.argv) == 1:
    from .shellMenu import main
    main()

else:
    from .cli import main
    main()
