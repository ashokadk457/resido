namespace Resido.Model.TTLockDTO.RequestDTO.EkeysRq
{

    /// <summary>
    /// Common interface for sending ekey fields.
    /// </summary>
    public interface ISendKeyRequest
    {
        int LockId { get; set; }
        string ReceiverUsername { get; set; }
        string KeyName { get; set; }
        long StartDate { get; set; }
        long EndDate { get; set; }
        string? Remarks { get; set; }
        int? RemoteEnable { get; set; }
        int? KeyRight { get; set; }
        int? CreateUser { get; set; }
    }

    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class SendKeyRequestDTO : ISendKeyRequest
    {
        public int LockId { get; set; }
        public string ReceiverUsername { get; set; }
        public string KeyName { get; set; }
        public long StartDate { get; set; }
        public long EndDate { get; set; }
        public string? Remarks { get; set; }
        public int? RemoteEnable { get; set; }
        public int? KeyRight { get; set; }
        public int? CreateUser { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockSendKeyRequestDTO : BaseRequestDTO, IAccessTokenRequest, ISendKeyRequest
    {
        public int LockId { get; set; }
        public string ReceiverUsername { get; set; }
        public string KeyName { get; set; }
        public long StartDate { get; set; }
        public long EndDate { get; set; }
        public string? Remarks { get; set; }
        public int? RemoteEnable { get; set; }
        public int? KeyRight { get; set; }
        public int? CreateUser { get; set; }
        public string AccessToken { get; set; }
    }

}
