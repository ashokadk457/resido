namespace Resido.Model.TTLockDTO.RequestDTO.PasscodeRq
{
    /// <summary>
    /// Client-facing request DTO (no access token).
    /// </summary>
    public class AddKeyboardPwdRequestDTO
    {
        public int LockId { get; set; }

        /// <summary>
        /// Custom passcode (4–9 digits).
        /// </summary>
        public string KeyboardPwd { get; set; }

        /// <summary>
        /// Optional: name of the passcode.
        /// </summary>
        public string? KeyboardPwdName { get; set; }

        /// <summary>
        /// Optional: passcode type (2 = permanent, 3 = period, default = 3).
        /// </summary>
        public int? KeyboardPwdType { get; set; } = 3;

        /// <summary>
        /// Optional: start time when passcode becomes valid (timestamp in ms).
        /// Required if type = 3 (period).
        /// </summary>
        public long? StartDate { get; set; }

        /// <summary>
        /// Optional: end time when passcode expires (timestamp in ms).
        /// Required if type = 3 (period).
        /// </summary>
        public long? EndDate { get; set; }

        /// <summary>
        /// Method of adding passcode (1 = Bluetooth, 2 = Cloud).
        /// </summary>
        public AddType AddType { get; set; } = AddType.Cloud;
    }

    /// <summary>
    /// TTLock API request DTO (includes access token, clientId, date).
    /// </summary>
    public class TTLockAddKeyboardPwdRequestDTO : BaseRequestDTO, IAccessTokenRequest
    {
        public int LockId { get; set; }
        public string KeyboardPwd { get; set; }
        public string? KeyboardPwdName { get; set; }
        public int? KeyboardPwdType { get; set; }
        public long? StartDate { get; set; }
        public long? EndDate { get; set; }
        public int AddType { get; set; }
        public string AccessToken { get; set; }
    }

}
