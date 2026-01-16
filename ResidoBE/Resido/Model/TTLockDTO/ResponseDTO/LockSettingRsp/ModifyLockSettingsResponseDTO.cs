namespace Resido.Model.TTLockDTO.ResponseDTO.LockSettingRsp
{
    /// <summary>
    /// TTLock API response for modify lock settings.
    /// </summary>
    public class ModifyLockSettingsResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
