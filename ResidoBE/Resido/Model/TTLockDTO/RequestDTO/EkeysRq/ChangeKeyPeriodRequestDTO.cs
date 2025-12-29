namespace Resido.Model.TTLockDTO.RequestDTO.EkeysRq
{

    /// <summary>
    /// Common interface for key period update fields.
    /// </summary>
    public interface IKeyPeriodRequest
    {
        int KeyId { get; set; }
        long StartDate { get; set; }
        long EndDate { get; set; }
    }

    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class ChangeKeyPeriodRequestDTO : IKeyPeriodRequest
    {
        public int KeyId { get; set; }
        public long StartDate { get; set; }
        public long EndDate { get; set; }
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockChangeKeyPeriodRequestDTO : BaseRequestDTO, IAccessTokenRequest, IKeyPeriodRequest
    {
        public int KeyId { get; set; }
        public string AccessToken { get; set; }
        public long StartDate { get; set; }
        public long EndDate { get; set; }
    }

}
