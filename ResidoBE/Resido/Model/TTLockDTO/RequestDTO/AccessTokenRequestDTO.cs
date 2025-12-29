namespace Resido.Model.TTLockDTO.RequestDTO
{
    // For OAuth2 token retrieval API
    public class AccessTokenRequestDTO : BaseRequestDTO
    {
        public string Username { get; set; }
        public string Password { get; set; }
    }
}
