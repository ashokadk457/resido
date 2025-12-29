namespace Resido.Model.TTLockDTO.RequestDTO.EkeysRq
{
    /// <summary>
    /// Common interface for key update fields.
    /// </summary>
    public interface IKeyUpdateRequest
    {
        int KeyId { get; set; }
        string? KeyName { get; set; }
        int? RemoteEnable { get; set; }
    }


    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class UpdateKeyRequestDTO : IKeyUpdateRequest
    {
        public int KeyId { get; set; }
        public string? KeyName { get; set; }
        public int? RemoteEnable { get; set; }
    }
    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockUpdateKeyRequestDTO : BaseRequestDTO, IAccessTokenRequest, IKeyUpdateRequest
    {
        public int KeyId { get; set; }
        public string AccessToken { get; set; }
        public string? KeyName { get; set; }
        public int? RemoteEnable { get; set; }
    }

}
