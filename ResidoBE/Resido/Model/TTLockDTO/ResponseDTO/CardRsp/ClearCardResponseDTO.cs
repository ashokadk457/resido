namespace Resido.Model.TTLockDTO.ResponseDTO.CardRsp
{
    /// <summary>
    /// TTLock API response for clear card.
    /// </summary>
    public class ClearCardResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }

}
