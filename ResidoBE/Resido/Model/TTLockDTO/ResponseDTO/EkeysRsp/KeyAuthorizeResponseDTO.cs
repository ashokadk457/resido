namespace Resido.Model.TTLockDTO.ResponseDTO.EkeysRsp
{
    /// <summary>
    /// TTLock API response for key authorization.
    /// </summary>
    public class KeyAuthorizeResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
