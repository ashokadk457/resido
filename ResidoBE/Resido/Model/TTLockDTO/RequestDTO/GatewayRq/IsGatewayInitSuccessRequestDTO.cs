namespace Resido.Model.TTLockDTO.RequestDTO.GatewayRq
{
    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class IsGatewayInitSuccessRequestDTO
    {
        /// <summary>
        /// The network MAC of the gateway, obtained when adding via APP SDK.
        /// </summary>
        public string GatewayNetMac { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockIsGatewayInitSuccessRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public string GatewayNetMac { get; set; }
        public string AccessToken { get; set; }
    }
}
