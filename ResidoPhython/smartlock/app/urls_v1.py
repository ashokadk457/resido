from app.controllers.keys_controller import get_keys, create_key, delete_key, list_ekeys
from app.controllers.account_controller import LoginUsernamePassword

from django.urls import path
from app.controllers.keys_controller import get_keys, create_key, delete_key, list_ekeys

urlpatterns = [
     path('Ekeys/get_all_ekeys', get_keys),
     path('Ekeys/create_ekey', create_key, name='create-key'),
     path('Ekeys/delete_ekey/<uuid:key_id>', delete_key, name='delete-key'),
     path("Ekeys/list_ekeys", list_ekeys, name="list-ekeys"),
     path(
        "Account/login_username_password",
        LoginUsernamePassword,
        name="login_username_password",
    ),
]