torrentClient
=============

References:
http://www.kristenwidman.com/blog/how-to-write-a-bittorrent-client-part-1/
https://wiki.theory.org/BitTorrentSpecification
http://bittorrent.org/beps/bep_0003.html
piazza
python docs (sockets, strings, ect ect)

Authors:
Connor Brinkmann
James Liu

Operation:
-Make sure that python bencoding library is installed using some kind of package manager
-Navigate to the folder containing the project and python script
-Select number of peers in python file at line 70
-run the python script using standard python interpreter with the torrent file as an argument:

Example: "python torrentClient.py ubuntu.iso.torrent"

Capabilities:
-Can decode torrent files
-Can dynamically query trackers using peerlist. (Two trackers tested, Ubuntu submits peer list, pirate bay returns connection refused.)
-Can connect to peers and issue requests
-Can decode requests
-Can build finished files (Single files only)
-Is Multithreaded

Notes:
-If only a singular peer is used, the peer thread will give up if the peer gives a bad handshake. So try multiple times in order to
find a good peer with a singular peer thread.
