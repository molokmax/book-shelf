# Simple in‑memory state store for each VK user while they are adding a book.
# Structure:
#   {
#       user_id: {
#           "command": str,
#           "state": str,
#          "data": {
#               "title": str,
#               "author": str,
#               "tags": list[str],
#              "pages": int
#           }
#       }
#   }
# Later we can move state storage to database

active_states = {}
