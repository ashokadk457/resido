using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Resido.Database.DBTable
{
    [Table("Country")]
    public class Country
    {
        [Key]
        public Guid Id { get; set; }
        public string Name { get; set; }
        public string Iso { get; set; } //Iso
        public string Iso3 { get; set; }
        public string PhoneCode { get; set; }
        public RowStatus Status { get; set; }
    }
}
