from docutils.nodes import literal

def setup(app):
    app.add_generic_role('api', literal)
    app.add_generic_role('source', literal)
