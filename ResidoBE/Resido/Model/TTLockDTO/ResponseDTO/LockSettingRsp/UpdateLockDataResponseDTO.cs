namespace Resido.Model.TTLockDTO.ResponseDTO.LockSettingRsp
{
    /// <summary>
    /// TTLock API response for update lock data.
    /// </summary>
    public class UpdateLockDataResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
