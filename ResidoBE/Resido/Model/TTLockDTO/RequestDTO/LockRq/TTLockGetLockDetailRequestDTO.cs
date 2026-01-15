namespace Resido.Model.TTLockDTO.RequestDTO.LockRq
{
    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockGetLockDetailRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public int LockId { get; set; }
        public string AccessToken { get; set; }
    }

}
