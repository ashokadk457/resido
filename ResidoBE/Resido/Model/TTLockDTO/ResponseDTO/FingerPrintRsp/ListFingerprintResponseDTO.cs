using Resido.Model.TTLockDTO.RequestDTO.CardRq;

namespace Resido.Model.TTLockDTO.ResponseDTO.FingerPrintRsp
{
    /// <summary>
    /// Represents a single fingerprint record.
    /// </summary>
    public class FingerprintRecordDTO
    {
        public int FingerprintId { get; set; }
        public int LockId { get; set; }
        public string FingerprintNumber { get; set; }
        public int FingerprintType { get; set; }
        public string? FingerprintName { get; set; }
        public long StartDate { get; set; }
        public long EndDate { get; set; }
        public long CreateDate { get; set; }
        public string SenderUsername { get; set; }
        public List<CyclicConfigDTO>? CyclicConfig { get; set; }
    }

    /// <summary>
    /// TTLock API response for list fingerprints.
    /// </summary>
    public class ListFingerprintResponseDTO
    {
        public List<FingerprintRecordDTO> List { get; set; }
        public int PageNo { get; set; }
        public int PageSize { get; set; }
        public int Pages { get; set; }
        public int Total { get; set; }
    }
}
