def version():
    import pkg_resources  # part of setuptools
    version = pkg_resources.require("gcdt")[0].version
    print(("gcdt version %s") % (version))