from app.controllers.keys_controller import get_keys, create_key, delete_key, list_ekeys
from app.controllers.account_controller import LoginUsernamePassword

from django.urls import path
from app.controllers.keys_controller import get_keys, create_key, delete_key, list_ekeys

urlpatterns = [
     path('Ekeys/getAllEKeys', get_keys),
     path('Ekeys/createKey', create_key, name='create-key'),
     path('Ekeys/deleteEKey/<uuid:key_id>', delete_key, name='delete-key'),
     path("Ekeys/listEKeys", list_ekeys, name="list-ekeys"),
     path(
        "Account/LoginUsernamePassword",
        LoginUsernamePassword,
        name="login_username_password",
    ),
]