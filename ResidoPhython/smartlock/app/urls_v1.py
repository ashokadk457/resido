from app.controllers.keys_controller import get_keys, create_key, delete_key, list_ekeys

from django.urls import path
from app.controllers.keys_controller import get_keys, create_key, delete_key, list_ekeys
from app.controllers.ttlock_token_controller import ttlock_token_view
urlpatterns = [
     path('Ekeys/getAllEKeys', get_keys),
     path('Ekeys/createKey', create_key, name='create-key'),
     path('Ekeys/deleteEKey/<uuid:key_id>', delete_key, name='delete-key'),
     path("Ekeys/listEKeys", list_ekeys, name="list-ekeys"),
     path('ttlock/token', ttlock_token_view, name='ttlock-token'),
]