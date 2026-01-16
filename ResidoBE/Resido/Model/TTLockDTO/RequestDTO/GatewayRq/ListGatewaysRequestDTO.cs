namespace Resido.Model.TTLockDTO.RequestDTO.GatewayRq
{
    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class ListGatewaysRequestDTO
    {
        /// <summary>
        /// Page number, starting from 1.
        /// </summary>
        public int PageNo { get; set; } = 1;

        /// <summary>
        /// Items per page, max 200.
        /// </summary>
        public int PageSize { get; set; } = 20;

        /// <summary>
        /// Sort order: 0 = by name, 1 = reverse order by time, 2 = reverse order by name.
        /// </summary>
        public int OrderBy { get; set; } = 1;
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockListGatewaysRequestDTO : BaseRequestDTO, IAccessTokenRequest, IPagingRequest
    {
        public int PageNo { get; set; }
        public int PageSize { get; set; }
        public int OrderBy { get; set; }
        public string AccessToken { get; set; }
    }

}
