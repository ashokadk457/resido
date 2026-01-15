namespace Resido.Model.TTLockDTO.ResponseDTO.LockRsp
{
    /// <summary>
    /// Represents a single lock record.
    /// </summary>
    public class LockRecordDTO
    {
        public int LockId { get; set; }
        public string LockName { get; set; }
        public string LockAlias { get; set; }
        public string LockMac { get; set; }
        public int ElectricQuantity { get; set; }
        public string FeatureValue { get; set; }
        public int HasGateway { get; set; }
        public string LockData { get; set; }
        public int GroupId { get; set; }
        public string GroupName { get; set; }
        public long Date { get; set; }
    }

    /// <summary>
    /// TTLock API response for list locks.
    /// </summary>
    public class ListLocksResponseDTO
    {
        public List<LockRecordDTO> List { get; set; }
        public int PageNo { get; set; }
        public int PageSize { get; set; }
        public int Pages { get; set; }
        public int Total { get; set; }
    }
}
