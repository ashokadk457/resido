namespace Resido.Model.TTLockDTO.RequestDTO.EkeysRq
{
    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class KeyUnauthorizeRequestDTO : IKeyAuthorizeRequest
    {
        public int LockId { get; set; }
        public int KeyId { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockKeyUnauthorizeRequestDTO : BaseRequestDTO, IAccessTokenRequest, IKeyAuthorizeRequest
    {
        public int LockId { get; set; }
        public int KeyId { get; set; }
        public string AccessToken { get; set; }
    }

}
