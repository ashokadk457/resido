namespace Resido.Model.TTLockDTO.ResponseDTO.PasscodeRsp
{
    /// <summary>
    /// TTLock API response for add custom passcode.
    /// </summary>
    public class AddKeyboardPwdResponseDTO: ResponseCodeDTO
    {
        /// <summary>
        /// Unique ID of the created passcode.
        /// </summary>
        public int KeyboardPwdId { get; set; }
    }

}
