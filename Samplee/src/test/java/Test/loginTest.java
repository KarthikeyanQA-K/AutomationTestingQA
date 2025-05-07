package Test;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.annotations.Test;

public class loginTest {
	@Test
	 public void login() {
	        

	        // Initialize WebDriver
	        WebDriver driver = new ChromeDriver();

	       
	            // Open the login page
	            driver.get("https://www.cflowapps.com/stage-signup/");

	            // Maximize the browser window
	            driver.manage().window().maximize();
System.out.println("suuesss");
System.out.println("suuesss");
System.out.println("suuesss");
	    }
	}

