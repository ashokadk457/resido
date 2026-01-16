namespace Resido.Model.TTLockDTO.RequestDTO.GatewayRq
{
    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockListGatewaysByLockRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public int LockId { get; set; }
        public string AccessToken { get; set; }
    }

}
