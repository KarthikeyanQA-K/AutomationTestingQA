

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver; 

public class LoginTest {

    public static void main(String[] args) {
        

        // Initialize WebDriver
        WebDriver driver = new ChromeDriver();

       
            // Open the login page
            driver.get("https://www.google.com/");

            // Maximize the browser window
            driver.manage().window().maximize();

    }
}
