namespace Resido.Model.TTLockDTO.RequestDTO.CardRq
{
    /// <summary>
    /// Defines recurring time period for cyclic cards.
    /// </summary>
    public class CyclicConfigDTO
    {
        /// <summary>
        /// Week day: 1 = Monday, 2 = Tuesday ... 7 = Sunday.
        /// </summary>
        public int WeekDay { get; set; }

        /// <summary>
        /// Start time in minutes (e.g., 480 = 8:00).
        /// </summary>
        public int StartTime { get; set; }

        /// <summary>
        /// End time in minutes (e.g., 1080 = 18:00).
        /// </summary>
        public int EndTime { get; set; }
    }

    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class AddCardRequestDTO
    {
        public int LockId { get; set; }

        /// <summary>
        /// Card number (from APP SDK or card reader).
        /// </summary>
        public string CardNumber { get; set; }

        /// <summary>
        /// Optional: card name.
        /// </summary>
        public string? CardName { get; set; }

        /// <summary>
        /// Start time when card becomes valid (timestamp in ms).
        /// </summary>
        public long StartDate { get; set; }

        /// <summary>
        /// End time when card expires (timestamp in ms).
        /// </summary>
        public long EndDate { get; set; }

        /// <summary>
        /// Card type: 1 = normal, 4 = cyclic (default = 1).
        /// </summary>
        public int CardType { get; set; } = 1;

        /// <summary>
        /// Optional: recurring time period for cyclic cards.
        /// </summary>
        public List<CyclicConfigDTO>? CyclicConfig { get; set; }

        /// <summary>
        /// Method of adding card (1 = Bluetooth, 2 = Cloud).
        /// </summary>
        public AddType AddType { get; set; } = AddType.Cloud;
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockAddCardRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public int LockId { get; set; }
        public string CardNumber { get; set; }
        public string? CardName { get; set; }
        public long StartDate { get; set; }
        public long EndDate { get; set; }
        public int CardType { get; set; }
        public List<CyclicConfigDTO>? CyclicConfig { get; set; }
        public int AddType { get; set; }
        public string AccessToken { get; set; }
    }

}
