namespace Resido.Model.TTLockDTO.RequestDTO.GatewayRq
{

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockListGatewayLocksRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public int GatewayId { get; set; }
        public string AccessToken { get; set; }
    }

}
