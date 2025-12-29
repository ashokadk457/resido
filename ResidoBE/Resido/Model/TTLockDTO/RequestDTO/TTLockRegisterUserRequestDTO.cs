namespace Resido.Model.TTLockDTO.RequestDTO
{
    // For user registration API
    public class TTLockRegisterUserRequestDTO : TTLockBaseRequestDTO
    {
        public string Username { get; set; }
        public string Password { get; set; }
    }
}
