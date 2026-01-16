namespace Resido.Model.TTLockDTO.ResponseDTO.GatewayRsp
{
    /// <summary>
    /// TTLock API response for setting gateway upgrade mode.
    /// </summary>
    public class SetGatewayUpgradeModeResponseDTO : ITTLockErrorResponse
    {
        public int Errcode { get; set; }
        public string Errmsg { get; set; }
    }
}
