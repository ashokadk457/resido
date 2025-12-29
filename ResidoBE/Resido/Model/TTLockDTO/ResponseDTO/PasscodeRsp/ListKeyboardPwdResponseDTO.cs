namespace Resido.Model.TTLockDTO.ResponseDTO.PasscodeRsp
{
    /// <summary>
    /// Represents a single passcode record.
    /// </summary>
    public class KeyboardPwdRecordDTO
    {
        public int KeyboardPwdId { get; set; }
        public int LockId { get; set; }
        public string KeyboardPwd { get; set; }
        public string? KeyboardPwdName { get; set; }
        public int KeyboardPwdType { get; set; }
        public long StartDate { get; set; }
        public long EndDate { get; set; }
        public long SendDate { get; set; }
        public int IsCustom { get; set; }
        public string SenderUsername { get; set; }
    }

    /// <summary>
    /// TTLock API response for listKeyboardPwd.
    /// </summary>
    public class ListKeyboardPwdResponseDTO : ResponseCodeDTO
    {
        public List<KeyboardPwdRecordDTO> List { get; set; }
        public int PageNo { get; set; }
        public int PageSize { get; set; }
        public int Pages { get; set; }
        public int Total { get; set; }
    }

}
