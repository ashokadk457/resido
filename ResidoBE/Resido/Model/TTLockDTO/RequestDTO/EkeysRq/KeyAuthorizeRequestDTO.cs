namespace Resido.Model.TTLockDTO.RequestDTO.EkeysRq
{
    /// <summary>
    /// Common interface for key authorization fields.
    /// </summary>
    public interface IKeyAuthorizeRequest
    {
        int LockId { get; set; }
        int KeyId { get; set; }
    }

    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class KeyAuthorizeRequestDTO : IKeyAuthorizeRequest
    {
        public int LockId { get; set; }
        public int KeyId { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockKeyAuthorizeRequestDTO : BaseRequestDTO, IAccessTokenRequest, IKeyAuthorizeRequest
    {
        public int LockId { get; set; }
        public int KeyId { get; set; }
        public string AccessToken { get; set; }
    }
}
