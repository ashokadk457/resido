namespace Resido.Model.TTLockDTO.RequestDTO.LockRq
{
    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class InitializeLockRequestDTO
    {
        /// <summary>
        /// Lock alias (optional).
        /// </summary>
        public string? LockAlias { get; set; }

        public string Mac { get; set; }
        /// <summary>
        /// Lock data (must be obtained from APP SDK callback).
        /// </summary>
        public string LockData { get; set; }

        /// <summary>
        /// Optional: group ID, refer to cloud API Add group.
        /// </summary>
        public int? GroupId { get; set; }

        /// <summary>
        /// Optional: NB-IoT lock init success flag (1 = yes, 0 = no).
        /// Only required for NB-IoT locks.
        /// </summary>
        public int? NbInitSuccess { get; set; }

        public string Category { get; set;}
        public string Location { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockInitializeLockRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public string? LockAlias { get; set; }
        public string LockData { get; set; }
        public int? GroupId { get; set; }
        public int? NbInitSuccess { get; set; }
        public string AccessToken { get; set; }
    }
}
