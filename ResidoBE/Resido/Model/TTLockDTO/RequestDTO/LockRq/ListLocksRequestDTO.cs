namespace Resido.Model.TTLockDTO.RequestDTO.LockRq
{
    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class ListLocksRequestDTO
    {
        /// <summary>
        /// Optional: search by lock alias (fuzzy matching).
        /// </summary>
        public string? LockAlias { get; set; }

        /// <summary>
        /// Optional: search by group ID.
        /// </summary>
        public int? GroupId { get; set; }

        /// <summary>
        /// Page number, starting from 1.
        /// </summary>
        public int PageNo { get; set; } = 1;

        /// <summary>
        /// Items per page, default 20, max 1000.
        /// </summary>
        public int PageSize { get; set; } = 20;

        /// <summary>
        /// Optional: type (1 = lock list, 2 = lift control list, 3 = power saver list).
        /// </summary>
        public int? Type { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockListLocksRequestDTO : BaseRequestDTO, IAccessTokenRequest, IPagingRequest
    {
        public string? LockAlias { get; set; }
        public int? GroupId { get; set; }
        public int PageNo { get; set; }
        public int PageSize { get; set; }
        public int? Type { get; set; }
        public string AccessToken { get; set; }
    }

}
