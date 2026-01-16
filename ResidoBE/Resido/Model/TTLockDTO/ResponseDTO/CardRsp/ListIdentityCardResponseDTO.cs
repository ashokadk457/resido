using Resido.Model.TTLockDTO.RequestDTO.CardRq;

namespace Resido.Model.TTLockDTO.ResponseDTO.CardRsp
{
    /// <summary>
    /// Represents a single IC card record.
    /// </summary>
    public class IdentityCardRecordDTO
    {
        public int CardId { get; set; }
        public int LockId { get; set; }
        public string CardNumber { get; set; }
        public string? CardName { get; set; }
        public int CardType { get; set; }
        public long StartDate { get; set; }
        public long EndDate { get; set; }
        public long CreateDate { get; set; }
        public string SenderUsername { get; set; }
        public List<CyclicConfigDTO>? CyclicConfig { get; set; }
        public bool IsExpired { get; set; }
        public bool IsExpiringSoon { get; set; }
    }

    /// <summary>
    /// TTLock API response for list identity cards.
    /// </summary>
    public class ListIdentityCardResponseDTO: ResponseCodeDTO
    {
        public List<IdentityCardRecordDTO> List { get; set; }
        public int PageNo { get; set; }
        public int PageSize { get; set; }
        public int Pages { get; set; }
        public int Total { get; set; }
    }

}
