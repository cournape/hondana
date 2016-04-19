import base64
import os
import sys

import jinja2


def main(argv=None):
    argv = argv or sys.argv[1:]

    template_path = argv[0]
    output = argv[1]

    with open(template_path) as fp:
        data = fp.read()

    template = jinja2.Template(data)
    secret = base64.b64encode(os.urandom(24))

    with open(output, "wt") as fp:
        fp.write(template.render(secret=secret))


if __name__ == "__main__":
    main()
