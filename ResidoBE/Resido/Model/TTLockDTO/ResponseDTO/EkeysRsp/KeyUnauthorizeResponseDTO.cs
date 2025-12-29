namespace Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp
{
    /// <summary>
    /// TTLock API response for cancel key authorization.
    /// </summary>
    public class KeyUnauthorizeResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
