# PolyClash: A Go-like game on sphere by using a snub dodecahedron board

## Introduction

Like mathematical truth, Go is an eternal game in the universe. Similarly, the snub dodecahedron is also an eternal geometric shape, which is the Archimedean polyhedron with the most sphericity.
We combine these two to create a new game: PolyClash.

Can we create a set of rules that are as simple as possible while making this game very interesting? So that this game is also an eternal game. This is our goal.

## Install

```bash
pip install polyclash
```

## Usage

The client can be started by running the following command:

```bash
polyclash-client
```

The client is a Qt application that allows you to play the game.

The local server can be started by running the following command:

```bash
polyclash-server
```

It should be noted that the server is not necessary to play the game.
The server is only needed if you want to play the game with other players in a local network.

## Deployment on a production server

You can also set up a production server, which can be accessed by other players on the internet.
We recommend using a reverse proxy like Nginx to set up the production server, and using uwsgi or similar tools
to run the server.

below is an example of how to run the server using uwsgi:

```bash
uwsgi --http :7763 --gevent 100 --http-websockets --master --wsgi polyclash.server:app --logto ~/.polyclash/uwsgi.log
```

and the Nginx configuration:

```nginx
server {
    listen 80;
    server_name polyclash.example.com;

    location /sphgo {
        proxy_pass http://127.0.0.1:7763;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_redirect off;
        proxy_buffering off;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
            
        proxy_pass http://127.0.0.1:7763/socket.io;
    }
}
```

## Development

How to release a new version:

```bash
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*

git tag va.b.c master
git push origin va.b.c
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
