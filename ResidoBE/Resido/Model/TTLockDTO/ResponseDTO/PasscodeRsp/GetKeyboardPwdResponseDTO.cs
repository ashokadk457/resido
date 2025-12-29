namespace Resido.Model.TTLockDTO.ResponseDTO.PasscodeRsp
{
    /// <summary>
    /// TTLock API response for get passcode.
    /// </summary>
    public class GetKeyboardPwdResponseDTO : ResponseCodeDTO
    {
        /// <summary>
        /// Generated passcode string.
        /// </summary>
        public string KeyboardPwd { get; set; }

        /// <summary>
        /// Unique ID of the generated passcode.
        /// </summary>
        public int KeyboardPwdId { get; set; }
    }
}
