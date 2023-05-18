from livereload import Server

from render_website import reload_index


# def main():
reload_index(1)
server = Server()
server.watch('template.html', reload_index(2))
server.serve(root='.')


# if __name__ == '__main__':
#     main()