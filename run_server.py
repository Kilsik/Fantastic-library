from livereload import Server

from render_website import reload_index


reload_index(1)
server = Server()
server.watch('template.html', reload_index(2))
server.serve(root='.')


