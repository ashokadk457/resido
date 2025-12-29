namespace Resido.Model.TTLockDTO.RequestDTO
{
    // For user registration API
    public class RegisterUserRequestDTO : BaseRequestDTO
    {
        public string Username { get; set; }
        public string Password { get; set; }
    }
}
