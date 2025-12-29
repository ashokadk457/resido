namespace Resido.Model.TTLockDTO.RequestDTO
{
    // For password reset API
    public class ResetPasswordRequestDTO : BaseRequestDTO
    {
        public string Username { get; set; }
        public string Password { get; set; }
    }
}
