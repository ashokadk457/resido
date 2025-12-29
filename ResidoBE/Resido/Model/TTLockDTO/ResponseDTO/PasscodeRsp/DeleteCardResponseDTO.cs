namespace Resido.Model.TTLockDTO.ResponseDTO.PasscodeRsp
{
    /// <summary>
    /// TTLock API response for delete card.
    /// </summary>
    public class DeleteCardResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
