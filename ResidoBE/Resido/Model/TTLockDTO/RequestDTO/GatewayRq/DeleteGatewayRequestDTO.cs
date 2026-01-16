namespace Resido.Model.TTLockDTO.RequestDTO.GatewayRq
{
    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class DeleteGatewayRequestDTO
    {
        /// <summary>
        /// Gateway ID to delete.
        /// </summary>
        public int GatewayId { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockDeleteGatewayRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public int GatewayId { get; set; }
        public string AccessToken { get; set; }
    }
}
