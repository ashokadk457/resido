namespace Resido.Model.TTLockDTO.RequestDTO.EkeysRq
{
    public class EkeysRequestDTO: PagingRequest
    {
        /// <summary>
        /// Optional: search by lock alias (fuzzy match)
        /// </summary>
        public string? LockAlias { get; set; }

        /// <summary>
        /// Optional: filter by group ID
        /// </summary>
        public int? GroupId { get; set; }
    }

}
