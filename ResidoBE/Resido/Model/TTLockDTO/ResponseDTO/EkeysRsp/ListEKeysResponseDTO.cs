namespace Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp
{
    /// <summary>
    /// Represents a single eKey record.
    /// </summary>
    public class EKeyRecordDTO
    {
        public int KeyId { get; set; }
        public int LockId { get; set; }
        public string Username { get; set; }
        public int Uid { get; set; }
        public string KeyName { get; set; }
        public string KeyStatus { get; set; }
        public long StartDate { get; set; }
        public long EndDate { get; set; }
        public int KeyRight { get; set; }
        public int RemoteEnable { get; set; }
        public string SenderUsername { get; set; }
        public string? Remarks { get; set; }
        public long Date { get; set; }
        public bool IsExpired { get; set; }
        public bool IsExpiringSoon { get; set; }
    }

    /// <summary>
    /// TTLock API response for list eKeys.
    /// </summary>
    public class ListEKeysResponseDTO : ResponseCodeDTO
    {
        public List<EKeyRecordDTO> List { get; set; }
        public int PageNo { get; set; }
        public int PageSize { get; set; }
        public int Pages { get; set; }
        public int Total { get; set; }
    }

}
