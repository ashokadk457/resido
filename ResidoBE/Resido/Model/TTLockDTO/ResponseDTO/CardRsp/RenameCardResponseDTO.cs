namespace Resido.Model.TTLockDTO.ResponseDTO.CardRsp
{
    /// <summary>
    /// TTLock API response for rename card.
    /// </summary>
    public class RenameCardResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
