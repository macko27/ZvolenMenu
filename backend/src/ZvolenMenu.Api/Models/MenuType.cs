namespace ZvolenMenu.Api.Models;

public class MenuType
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;

    public ICollection<Meal> Meals { get; set; } = new List<Meal>();
}
